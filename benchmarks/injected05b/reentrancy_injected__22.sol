pragma solidity 0.5.12;

contract Wallet3317 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        credit[msg.sender] -= amount;
        reserve -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
