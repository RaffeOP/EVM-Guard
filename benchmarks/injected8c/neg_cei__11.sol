pragma solidity 0.8.20;

contract Safe5739 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        credit[msg.sender] -= amount;
        reserve -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
