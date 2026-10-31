pragma solidity 0.5.12;

contract Locker5524 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        total += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
