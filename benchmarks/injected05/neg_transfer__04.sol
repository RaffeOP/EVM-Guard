pragma solidity 0.5.12;

contract Wallet1994 {
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
        msg.sender.transfer(amount);
        shares[msg.sender] -= amount;
        reserve -= amount;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }
}
