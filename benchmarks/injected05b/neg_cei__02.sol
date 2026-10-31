pragma solidity 0.5.12;

contract Safe2784 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        shares[msg.sender] -= amount;
        reserve -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function ownerOf_() public view returns (address) { return owner; }
}
